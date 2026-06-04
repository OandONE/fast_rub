import os
from typing import Optional
from dataclasses import dataclass
from .database import DataBase
from ..utils.encryption import Encryption

SUFFIX = "faru"


@dataclass
class SessionData:
    """کلاس داده‌ای برای نگهداری مقادیر session"""
    token: str
    user_agent: str | None = None
    time_out: float | None = None
    display_welcome: bool = False
    view_logs: bool = False
    save_logs: bool = False
    offset_id: str | None = None
    save_offset_id: bool = True


class Session:
    """
    مدیریت session با استفاده از DataBase.

    Usage:
        session = await Session.open("user123", token="abc")
        print(session.token)
        session.time_out = 60.0
        await session.save()
    """

    def __init__(self, name: str, data: SessionData, db: DataBase) -> None:
        self._name = name
        self._data = data
        self._db = db

    # ── Properties ──────────────────────────────────────────

    @property
    def token(self) -> str:
        return self._data.token

    @token.setter
    def token(self, value: str) -> None:
        self._data.token = value

    @property
    def user_agent(self) -> str | None:
        return self._data.user_agent

    @user_agent.setter
    def user_agent(self, value: str | None) -> None:
        self._data.user_agent = value

    @property
    def time_out(self) -> float | None:
        return self._data.time_out

    @time_out.setter
    def time_out(self, value: float | None) -> None:
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
    def offset_id(self, value: str | None) -> None:
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
        token: str | None = None,
        user_agent: str | None = None,
        time_out: float | None = None,
        display_welcome: bool | None = None,
        view_logs: bool | None = None,
        save_logs: bool | None = None,
        offset_id: str | None = None,
        save_offset_id: bool | None = None,
    ) -> "Session":
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
        token: str | None = None,
        user_agent: str | None = None,
        time_out: float | None = None,
        display_welcome: bool | None = None,
        view_logs: bool | None = None,
        save_logs: bool | None = None,
        offset_id: str | None = None,
        save_offset_id: bool | None = None,
    ) -> "Session":
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

        path = cls._make_path(name)
        db = DataBase(path)

        await db.start(tables={
            "session": {
                "token": "TEXT NOT NULL",
                "user_agent": "TEXT",
                "time_out": "REAL",
                "display_welcome": "INTEGER NOT NULL DEFAULT 0",
                "view_logs": "INTEGER NOT NULL DEFAULT 0",
                "save_logs": "INTEGER NOT NULL DEFAULT 0",
                "offset_id": "TEXT",
                "save_offset_id": "INTEGER NOT NULL DEFAULT 1",
            }
        })

        session = cls(name, data, db)
        await session.save()
        return session

    async def save(self) -> None:
        save_token = Encryption.en(self._data.token)
        values = {
            "token": save_token,
            "user_agent": self._data.user_agent,
            "time_out": self._data.time_out,
            "display_welcome": int(self._data.display_welcome),
            "view_logs": int(self._data.view_logs),
            "save_logs": int(self._data.save_logs),
            "offset_id": self._data.offset_id,
            "save_offset_id": int(self._data.save_offset_id),
        }

        exists = await self._db.exists("session", {})
        if exists:
            await self._db.delete("session", {})
        await self._db.write("session", values)

    # ── Private Methods ─────────────────────────────────────

    @staticmethod
    def _make_path(name: str) -> str:
        return f"{name}.{SUFFIX}"

    @classmethod
    async def _open_existing(
        cls,
        name: str,
        token: str | None = None,
        user_agent: str | None = None,
        time_out: float | None = None,
        display_welcome: bool | None = None,
        view_logs: bool | None = None,
        save_logs: bool | None = None,
        offset_id: str | None = None,
        save_offset_id: bool | None = None,
    ) -> "Session":
        path = cls._make_path(name)
        db = DataBase(path)

        await db.start(tables={
            "session": {
                "token": "TEXT NOT NULL",
                "user_agent": "TEXT",
                "time_out": "REAL",
                "display_welcome": "INTEGER NOT NULL DEFAULT 0",
                "view_logs": "INTEGER NOT NULL DEFAULT 0",
                "save_logs": "INTEGER NOT NULL DEFAULT 0",
                "offset_id": "TEXT",
                "save_offset_id": "INTEGER NOT NULL DEFAULT 1",
            }
        })

        row = await db.find("session", "*")

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

        # تبدیل tuple به dict
        cols = ["token", "user_agent", "time_out", "display_welcome", "view_logs", "save_logs", "offset_id", "save_offset_id"]
        current = {}
        for i, col in enumerate(cols):
            current[col] = row[i]

        current["token"] = Encryption.de(current["token"])
        current["display_welcome"] = bool(current["display_welcome"])
        current["view_logs"] = bool(current["view_logs"])
        current["save_logs"] = bool(current["save_logs"])
        current["save_offset_id"] = bool(current["save_offset_id"])

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

        needs_save = False
        for key, new_value in updates.items():
            if new_value is not None and new_value != current[key]:
                current[key] = new_value
                needs_save = True

        data = SessionData(**current)
        session = cls(name, data, db)

        if needs_save:
            await session.save()

        return session
