from ..core.async_sync import wrap_all_async_methods

from typing import Optional, Literal, List, Dict, Any
from datetime import datetime
import aiosqlite
import asyncio
import logging
import shutil
import os


class DataBase:
    def __init__(
        self,
        db_name: str,
        timeout: float = 10,
        journal_mode: Literal["DELETE", "TRUNCATE", "PERSIST", "MEMORY", "WAL", "OFF", "ROLLBACK"] = "WAL",
        synchronous: Literal["OFF", "NORMAL", "FULL", "EXTRA"] = "NORMAL",
        logger: logging.Logger | None = None
    ) -> None:
        self.db_name = db_name
        self.timeout = timeout
        self.journal_mode = journal_mode
        self.synchronous = synchronous
        self.logger = logger or logging.getLogger("fast_rub.db")
        self.db_lock = asyncio.Lock()
        self._conn: aiosqlite.Connection | None = None

    async def connect_db(self) -> aiosqlite.Connection:
        return await aiosqlite.connect(self.db_name, timeout=self.timeout)
    
    async def _get_conn(self) -> aiosqlite.Connection:
        """connection رو برمی‌گردونه. اگه نیست یا بسته شده، می‌سازه."""
        if self._conn is None:
            self._conn = await self.connect_db()
        elif not self._conn.is_alive:
            await self._conn.close()
            self._conn = await self.connect_db()
        return self._conn
    
    async def close(self):
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def start(self, tables: dict = {}):
        """ساخت جداول و اضافه کردن ستون‌های جدید"""
        db = await self._get_conn()
        async with self.db_lock:
            for table_name, columns in tables.items():
                col_defs = []
                for col_name, col_type in columns.items():
                    col_defs.append(f"{col_name} {col_type}")
                
                command = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(col_defs)})"
                async with db.cursor() as cursor:
                    await cursor.execute(command)
                
                async with db.cursor() as cursor:
                    await cursor.execute(f"PRAGMA table_info({table_name})")
                    existing_cols = await cursor.fetchall()
                    existing_names = {row[1] for row in existing_cols}
                
                for col_name, col_type in columns.items():
                    if col_name not in existing_names:
                        default = "NULL"
                        if "PRIMARY KEY" in col_type.upper():
                            default = ""
                        else:
                            default = "NULL"
                        
                        try:
                            await cursor.execute(
                                f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type} DEFAULT {default}"
                            )
                            self.logger.info(f"✅ Column '{col_name}' added to '{table_name}'")
                        except aiosqlite.OperationalError:
                            pass
            
            await db.commit()
        # await db.close()
        self.logger.info(f"Database started with {len(tables)} tables.")

    async def find(
        self,
        tabel_name: str,
        result: str,
        where_values: dict = {}
    ):
        command = f"SELECT {result} FROM {tabel_name}"
        vals = []

        if where_values:
            where_parts = []
            for col, val in where_values.items():
                where_parts.append(f"{col} = ?")
                vals.append(val)
            command += f" WHERE {' AND '.join(where_parts)}"

        command += " LIMIT 1"

        try:
            db = await self._get_conn()
            async with self.db_lock:
                async with db.cursor() as cursor:
                    await cursor.execute(command, tuple(vals))
                    res = await cursor.fetchone()
                await db.commit()
            # await db.close()

            if res:
                return res[0] if len(res) == 1 else res
            return None
        except Exception as e:
            self.logger.error(f"Error in find: {e}")
            return None

    async def write(self, tabel_name: str, values: dict) -> bool:
        columns = list(values.keys())
        placeholders = ["?" for _ in columns]
        vals = list(values.values())

        command = f"""
            INSERT INTO {tabel_name}
            ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """

        try:
            db = await self._get_conn()
            async with self.db_lock:
                async with db.cursor() as cursor:
                    await cursor.execute(command, tuple(vals))
                    await db.commit()
            # await db.close()
            return True
        except Exception as e:
            self.logger.error(f"Error in write: {e}")
            return False

    async def update(self, tabel_name: str, set_values: dict, where_values: dict) -> bool:
        set_parts = []
        vals = []
        for col, val in set_values.items():
            set_parts.append(f"{col} = ?")
            vals.append(val)

        where_parts = []
        for col, val in where_values.items():
            where_parts.append(f"{col} = ?")
            vals.append(val)

        command = f"""
            UPDATE {tabel_name}
            SET {', '.join(set_parts)}
            WHERE {' AND '.join(where_parts)}
        """

        try:
            db = await self._get_conn()
            async with self.db_lock:
                async with db.cursor() as cursor:
                    await cursor.execute(command, tuple(vals))
                    await db.commit()
            # await db.close()
            return True
        except Exception as e:
            self.logger.error(f"Error in update: {e}")
            return False

    async def delete(self, tabel_name: str, where_values: dict) -> bool:
        vals = []
        if not where_values:
            command = f"DELETE FROM {tabel_name}"
        else:
            where_parts = []
            for col, val in where_values.items():
                where_parts.append(f"{col} = ?")
                vals.append(val)

            command = f"""
                DELETE FROM {tabel_name}
                WHERE {' AND '.join(where_parts)}
            """

        try:
            db = await self._get_conn()
            async with self.db_lock:
                async with db.cursor() as cursor:
                    await cursor.execute(command, tuple(vals))
                    await db.commit()
            # await db.close()
            return True
        except Exception as e:
            self.logger.error(f"Error in delete: {e}")
            return False

    async def len_rows(self, tabel_name: str, where_values: dict = {}) -> int:
        command = f"SELECT COUNT(*) FROM {tabel_name}"
        vals = []

        if where_values:
            where_parts = []
            for col, val in where_values.items():
                if not (val is None):
                    where_parts.append(f"{col} = ?")
                    vals.append(val)
            command += f" WHERE {' AND '.join(where_parts)}"

        try:
            db = await self._get_conn()
            async with self.db_lock:
                async with db.cursor() as cursor:
                    await cursor.execute(command, tuple(vals))
                    result = await cursor.fetchone()
            # await db.close()
            return result[0] if result else 0
        except Exception as e:
            self.logger.error(f"Error in len_rows: {e}")
            return 0

    async def find_all(
        self,
        tabel_name: str,
        result: str = "*",
        where_values: dict = {},
        order_by: str | None = None,
        limit: int | None = None,
        offset: int | None = None
    ) -> list[tuple]:
        command = f"SELECT {result} FROM {tabel_name}"
        vals = []

        if where_values:
            where_parts = []
            for col, val in where_values.items():
                where_parts.append(f"{col} = ?")
                vals.append(val)
            command += f" WHERE {' AND '.join(where_parts)}"

        if order_by:
            command += f" ORDER BY {order_by}"

        if limit is not None:
            command += f" LIMIT {limit}"
        if offset is not None:
            command += f" OFFSET {offset}"

        try:
            db = await self._get_conn()
            async with self.db_lock:
                async with db.cursor() as cursor:
                    await cursor.execute(command, tuple(vals))
                    results = await cursor.fetchall()
            # await db.close()
            return list(results) if results else [] # type: ignore
        except Exception as e:
            self.logger.error(f"Error in find_all: {e}")
            return []

    async def exists(self, tabel_name: str, where_values: dict) -> bool:
        count = await self.len_rows(tabel_name, where_values)
        return count > 0

    async def increment(self, tabel_name: str, column: str, where_values: dict, amount: int = 1) -> bool:
        where_parts = []
        vals = [amount]

        for col, val in where_values.items():
            where_parts.append(f"{col} = ?")
            vals.append(val)

        command = f"""
            UPDATE {tabel_name}
            SET {column} = {column} + ?
            WHERE {' AND '.join(where_parts)}
        """

        try:
            db = await self._get_conn()
            async with self.db_lock:
                async with db.cursor() as cursor:
                    await cursor.execute(command, tuple(vals))
                    await db.commit()
            # await db.close()
            return True
        except Exception as e:
            self.logger.error(f"Error in increment: {e}")
            return False

    async def find_distinct(
        self,
        tabel_name: str,
        result: str,
        where_values: dict = {}
    ) -> list:
        command = f"SELECT DISTINCT {result} FROM {tabel_name}"
        vals = []

        if where_values:
            where_parts = []
            for col, val in where_values.items():
                where_parts.append(f"{col} = ?")
                vals.append(val)
            command += f" WHERE {' AND '.join(where_parts)}"

        try:
            db = await self._get_conn()
            async with self.db_lock:
                async with db.cursor() as cursor:
                    await cursor.execute(command, tuple(vals))
                    results = await cursor.fetchall()
            # await db.close()
            return [row[0] for row in results] if results else []
        except Exception as e:
            self.logger.error(f"Error in find_distinct: {e}")
            return []

    async def find_top_n(
        self,
        tabel_name: str,
        group_by: str,
        count_column: str = "COUNT(*)",
        where_values: dict = {},
        n: int = 3,
        order_desc: bool = True
    ) -> list[dict[str, Any]]:
        vals = []
        where_clause = ""
        if where_values:
            where_parts = []
            for col, val in where_values.items():
                where_parts.append(f"{col} = ?")
                vals.append(val)
            where_clause = f"WHERE {' AND '.join(where_parts)}"
        order_direction = "DESC" if order_desc else "ASC"
        command = f"""
            SELECT {group_by}, {count_column} as count_value
            FROM {tabel_name}
            {where_clause}
            GROUP BY {group_by}
            ORDER BY count_value {order_direction}
            LIMIT {n}
        """
        try:
            db = await self._get_conn()
            async with self.db_lock:
                async with db.cursor() as cursor:
                    await cursor.execute(command, tuple(vals))
                    results = await cursor.fetchall()
            # await db.close()
            return [
                {group_by: row[0], "count": row[1]}
                for row in results
            ] if results else []
        except Exception as e:
            self.logger.error(f"Error in find_top_n: {e}")
            return []

    async def add_column_if_not_exists(
        self,
        table: str,
        column: str,
        col_type: str,
        default: str = "NULL"
    ):
        try:
            db = await self._get_conn()
            async with self.db_lock:
                async with db.cursor() as cursor:
                    await cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type} DEFAULT {default}")
                    await db.commit()
            # await db.close()
            self.logger.info(f"Column '{column}' added to '{table}'")
        except aiosqlite.OperationalError:
            pass
        except Exception as e:
            self.logger.error(f"Error adding column {column}: {e}")
    
    async def backup(self, path: str | None = None) -> str:
        """بک‌آپ از دیتابیس"""
        if path is None:
            backup_dir = "backups"
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            db_name = os.path.splitext(os.path.basename(self.db_name))[0]
            path = os.path.join(backup_dir, f"{db_name}_{timestamp}.db")
        
        if self._conn:
            await self._conn.commit()
        
        await asyncio.to_thread(shutil.copy2, self.db_name, path)
        
        self.logger.info(f":white_check_mark: بک‌آپ ذخیره شد: {path}")
        return path
    
    async def restore(self, path: str) -> bool:
        """بازگردانی دیتابیس از بک‌آپ."""
        if not os.path.exists(path):
            self.logger.error(f":x: فایل بک‌آپ پیدا نشد: {path}")
            return False
        
        if self._conn:
            await self._conn.close()
            self._conn = None
        
        await asyncio.to_thread(shutil.copy2, path, self.db_name)
        
        self._conn = await self.connect_db()
        self.logger.info(f":white_check_mark: دیتابیس از بک‌آپ بازگردانی شد: {path}")
        return True

wrap_all_async_methods(DataBase)

