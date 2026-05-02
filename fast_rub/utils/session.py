import os
import aiosqlite
from typing import Optional
from dataclasses import dataclass
from .encryption import Encryption

SUFFIX = "faru"


@dataclass
class SessionData:
    """کلاس داده‌ای برای نگهداری مقادیر session"""
    token: str
    user_agent: Optional[str] = None
    time_out: Optional[float] = None
    display_welcome: bool = False
    view_logs: bool = False
    save_logs: bool = False
    offset_id: Optional[str] = None
    save_offset_id: bool = True


class Session:
    """
    مدیریت session با استفاده از SQLite.

    Usage:
        # باز کردن (یا ایجاد) session
        session = await Session.open("user123", token="abc")

        # خوندن مقادیر
        print(session.token)
        print(session.time_out)

        # تغییر مقادیر
        session.time_out = 60.0
        await session.save()

        # یا باز کردن با مقادیر جدید
        session = await Session.open("user123", time_out=30.0)
    """

    def __init__(self, name: str, data: SessionData) -> None:
        self._name = name
        self._path = self._make_path(name)
        self._data = data

    # ── Properties ──────────────────────────────────────────

    @property
    def token(self) -> str:
        return self._data.token

    @token.setter
    def token(self, value: str) -> None:
        self._data.token = value

    @property
    def user_agent(self) -> Optional[str]:
        return self._data.user_agent

    @user_agent.setter
    def user_agent(self, value: Optional[str]) -> None:
        self._data.user_agent = value

    @property
    def time_out(self) -> Optional[float]:
        return self._data.time_out

    @time_out.setter
    def time_out(self, value: Optional[float]) -> None:
        self._data.time_out = value

    @property
    def display_welcome(self) -> bool:
        return self._data.display_welcome

    @display_welcome.setter
    def display_welcome(self, value: bool) -> None:
        self._data.display_welcome = value

    @property
    def view_logs(self) -> bool:
        return self._data.view_logs

    @view_logs.setter
    def view_logs(self, value: bool) -> None:
        self._data.view_logs = value

    @property
    def save_logs(self) -> bool:
        return self._data.save_logs

    @save_logs.setter
    def save_logs(self, value: bool) -> None:
        self._data.save_logs = value

    @property
    def offset_id(self) -> str:
        return self._data.offset_id if self._data.offset_id else ""

    @offset_id.setter
    def offset_id(self, value: Optional[str]) -> None:
        self._data.offset_id = value

    @property
    def save_offset_id(self) -> bool:
        return self._data.save_offset_id

    @save_offset_id.setter
    def save_offset_id(self, value: bool) -> None:
        self._data.save_offset_id = value

    # ── Public Methods ──────────────────────────────────────

    @classmethod
    async def open(
        cls,
        name: str,
        token: Optional[str] = None,
        user_agent: Optional[str] = None,
        time_out: Optional[float] = None,
        display_welcome: Optional[bool] = None,
        view_logs: Optional[bool] = None,
        save_logs: Optional[bool] = None,
        offset_id: Optional[str] = None,
        save_offset_id: Optional[bool] = None,
    ) -> "Session":
        """
        باز کردن session موجود یا ساخت جدید.

        اگه فایل دیتابیس وجود داشته باشه:
            مقادیر رو می‌خونه و فقط پارامترهای غیر None رو آپدیت می‌کنه.
        اگه فایل وجود نداشته باشه:
            متد create رو صدا می‌زنه.
        """
        path = cls._make_path(name)

        if os.path.isfile(path):
            return await cls._open_existing(
                name=name,
                token=token,
                user_agent=user_agent,
                time_out=time_out,
                display_welcome=display_welcome,
                view_logs=view_logs,
                save_logs=save_logs,
                offset_id=offset_id,
                save_offset_id=save_offset_id,
            )
        else:
            return await cls.create(
                name=name,
                token=token,
                user_agent=user_agent,
                time_out=time_out,
                display_welcome=display_welcome,
                view_logs=view_logs,
                save_logs=save_logs,
                offset_id=offset_id,
                save_offset_id=save_offset_id,
            )

    @classmethod
    async def create(
        cls,
        name: str,
        token: Optional[str] = None,
        user_agent: Optional[str] = None,
        time_out: Optional[float] = None,
        display_welcome: Optional[bool] = None,
        view_logs: Optional[bool] = None,
        save_logs: Optional[bool] = None,
        offset_id: Optional[str] = None,
        save_offset_id: Optional[bool] = None,
    ) -> "Session":
        """
        ساخت session جدید.

        اگه token مقدار نداشته باشه، از کاربر پرسیده میشه.
        """
        if token is None:
            token = input("Write The Token: ")

        data = SessionData(
            token=token,
            user_agent=user_agent,
            time_out=time_out,
            display_welcome=display_welcome if display_welcome is not None else False,
            view_logs=view_logs if view_logs is not None else False,
            save_logs=save_logs if save_logs is not None else False,
            offset_id=offset_id,
            save_offset_id=save_offset_id if save_offset_id is not None else True,
        )

        session = cls(name, data)
        await session._init_db()
        await session.save()
        return session

    async def save(self) -> None:
        """
        ذخیره مقادیر جاری session توی دیتابیس.
        چون جدول فقط یه ردیف داره، از INSERT OR REPLACE استفاده می‌کنیم.
        """
        data = self._data
        save_token = Encryption.en(data.token)

        async with aiosqlite.connect(self._path) as db:
            await db.execute("DELETE FROM session")
            await db.execute(
                """
                INSERT INTO session (
                    token, user_agent, time_out, display_welcome,
                    view_logs, save_logs, offset_id, save_offset_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    save_token,
                    data.user_agent,
                    data.time_out,
                    int(data.display_welcome),
                    int(data.view_logs),
                    int(data.save_logs),
                    data.offset_id,
                    int(data.save_offset_id),
                ),
            )
            await db.commit()

    # ── Private Methods ─────────────────────────────────────

    @staticmethod
    def _make_path(name: str) -> str:
        """مسیر فایل دیتابیس رو برمی‌گردونه."""
        return f"{name}.{SUFFIX}"

    async def _init_db(self) -> None:
        """ساخت جدول session اگه وجود نداره."""
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS session (
                    token TEXT NOT NULL,
                    user_agent TEXT,
                    time_out REAL,
                    display_welcome INTEGER NOT NULL DEFAULT 0,
                    view_logs INTEGER NOT NULL DEFAULT 0,
                    save_logs INTEGER NOT NULL DEFAULT 0,
                    offset_id TEXT,
                    save_offset_id INTEGER NOT NULL DEFAULT 1
                )
                """
            )
            await db.commit()

    @classmethod
    async def _open_existing(
        cls,
        name: str,
        token: Optional[str] = None,
        user_agent: Optional[str] = None,
        time_out: Optional[float] = None,
        display_welcome: Optional[bool] = None,
        view_logs: Optional[bool] = None,
        save_logs: Optional[bool] = None,
        offset_id: Optional[str] = None,
        save_offset_id: Optional[bool] = None,
    ) -> "Session":
        """
        باز کردن فایل موجود، خوندن مقادیر، و آپدیت کردن
        فقط پارامترهایی که None نیستن و با دیتابیس فرق دارن.
        """
        path = cls._make_path(name)
        needs_save = False

        async with aiosqlite.connect(path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM session LIMIT 1")
            row = await cursor.fetchone()

            if row is None:
                return await cls.create(
                    name=name,
                    token=token,
                    user_agent=user_agent,
                    time_out=time_out,
                    display_welcome=display_welcome,
                    view_logs=view_logs,
                    save_logs=save_logs,
                    offset_id=offset_id,
                    save_offset_id=save_offset_id,
                )

            current = {
                "token": Encryption.de(row["token"]),
                "user_agent": row["user_agent"],
                "time_out": row["time_out"],
                "display_welcome": bool(row["display_welcome"]),
                "view_logs": bool(row["view_logs"]),
                "save_logs": bool(row["save_logs"]),
                "offset_id": row["offset_id"],
                "save_offset_id": bool(row["save_offset_id"]),
            }

            updates = {
                "token": token,
                "user_agent": user_agent,
                "time_out": time_out,
                "display_welcome": display_welcome,
                "view_logs": view_logs,
                "save_logs": save_logs,
                "offset_id": offset_id,
                "save_offset_id": save_offset_id,
            }

            for key, new_value in updates.items():
                if new_value is not None and new_value != current[key]:
                    current[key] = new_value
                    needs_save = True

        data = SessionData(**current)
        session = cls(name, data)

        if needs_save:
            await session.save()

        return session

