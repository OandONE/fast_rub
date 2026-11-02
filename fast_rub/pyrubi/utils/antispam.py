"""
سیستم ضد اسپم یوزربات (Pyrubi) - Userbot anti-spam for Fast Rub.

این ماژول نسخهٔ توسعه‌یافتهٔ :class:`fast_rub.utils.antispam.AntiSpam` برای
یوزربات است. تشخیص اسپم همان قوانین نسخهٔ ربات است، اما این کلاس خودش
پیام :class:`fast_rub.pyrubi.types.Message` را می‌فهمد و اکشن مناسب را
(نادیده‌گرفتن، حذف، اخطار، سکوت موقت، بن) روی همان پیام اجرا می‌کند.

Usage::

    from fast_rub.pyrubi import Client, AntiSpam

    bot = Client(
        session="my_account",
        antispam=AntiSpam(action="delete"),
    )

    @bot.on_message()
    async def handler(msg):
        await msg.reply("پیام سالم")

نکته: برای فعال‌کردن سکوت واقعی در یوزربات، چون روبیکا متود اختصاصی
«میوت عضو» در اختیار اکانت کاربری نمی‌گذارد، اکشن ``mute`` عضو را
با ``banChatMember`` اخراج می‌کند و بعد از مدت قانون دوباره آنبن
می‌کند.
"""
from __future__ import annotations

import asyncio
import re
import time
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Literal, cast

from ...utils.antispam import (
    AntiSpam as _BaseAntiSpam,
    AntiSpamRule,
    SpamViolation,
)

if TYPE_CHECKING:
    from ..methods.methods import Methods
    from ..types import Message


Action = Literal["ignore", "delete", "warn", "mute", "ban"]

_VALID_ACTIONS = frozenset({"ignore", "delete", "warn", "mute", "ban"})


class AntiSpam(_BaseAntiSpam):
    """
    نسخهٔ یوزربات :class:`fast_rub.utils.antispam.AntiSpam`.

    همهٔ پارامترهای کلاس پایه (``flood_max``، ``rate_max``، ``mute_duration``
    و ...) پذیرفته می‌شوند و پارامترهای این کلاس به رفتار اجرایی آن اضافه
    می‌شوند:

    Parameters
    ----------
    enabled : bool = True
        فعال بودن کل سیستم (قابل تغییر در زمان اجرا با ``enable``/``disable``).

    action : str = "delete"
        اکشن پیش‌فرض هنگام تشخیص اسپم:
        ``ignore`` (فقط رد کردن پیام، بدون درخواست شبکه‌ای)،
        ``delete`` (حذف پیام)،
        ``warn`` (ارسال اخطار و سپس حذف)،
        ``mute`` (حذف + اخراج موقت با آنبن خودکار)،
        ``ban`` (حذف + اخراج دائمی).
        مقدار ``kick`` هم به عنوان نام دیگر ``mute`` پذیرفته می‌شود.

    actions : dict[SpamViolation | str, str] | None
        اکشن اختصاصی برای هر نوع تخلف؛ مثلاً
        ``{SpamViolation.LINK_SPAM: "mute"}``. کلید می‌تواند خود enum،
        ``value`` یا ``name`` آن باشد.

    mute_seconds : float | None
        مدت اخراج موقت برای اکشن ``mute``. اگر ``None`` باشد از
        ``mute_duration`` همان قانون استفاده می‌شود.

    warn_text : str
        متن اخطار. از ``{reason}``، ``{user}`` و ``{chat}`` پشتیبانی می‌کند.

    delete_on_action : bool = True
        پیام اسپم قبل از ``warn``/``mute``/``ban`` حذف شود.

    delete_during_mute : bool = True
        پیام‌های بعدی کاربر سکوت‌شده هم حذف شوند (برای اکشن ``ignore`` نه).

    ignore_admins : bool = True
        ادمین‌های گروه از بررسی معاف شوند (لیست ادمین‌ها کش می‌شود).

    ignore_bots : bool = True
        پیام‌های ارسال‌شده توسط ربات‌ها بررسی نشوند.

    check_private : bool = False
        پیام‌های پیوی هم بررسی شوند.

    check_channels : bool = False
        پست‌های کانال هم بررسی شوند (اکشن‌های بن برای کانال اجرا نمی‌شوند).

    check_edited : bool = False
        پیام‌های ویرایش‌شده هم بررسی شوند.

    chats : Iterable[str] | None
        اگر داده شود فقط همین چت‌ها بررسی می‌شوند.

    ignore_chats : Iterable[str] | None
        این چت‌ها هرگز بررسی نمی‌شوند.

    admin_cache_ttl : float = 300.0
        مدت کش لیست ادمین‌های هر گروه (ثانیه). صفر = بدون کش.

    max_admin_pages : int = 100
        حداکثر تعداد صفحه برای دریافت لیست ادمین‌های یک گروه.

    shutdown_timeout : float = 5.0
        حداکثر زمان تلاش برای آنبن کردن سکوت‌های موقت هنگام خاموشی.
    """

    # الگوی گسترده‌تر لینک برای یوزربات؛ علاوه بر rubika.ir، آدرس‌های معمول
    # (http/https/www و دامنه‌های رایج) را هم به عنوان لینک می‌شمارد.
    RUBIKA_LINK = re.compile(
        r"(?:https?://|www\.)\S+"
        r"|(?:[a-zA-Z0-9-]+\.)+(?:ir|com|net|org|io|me|co|app|dev|xyz|info|site|online)\b\S*",
        re.IGNORECASE,
    )

    def __init__(
        self,
        *,
        enabled: bool = True,
        action: Action = "delete",
        actions: dict[SpamViolation | str, Action] | None = None,
        mute_seconds: float | None = None,
        warn_text: str = "🚫 {reason}",
        delete_on_action: bool = True,
        delete_during_mute: bool = True,
        ignore_admins: bool = True,
        ignore_bots: bool = True,
        check_private: bool = False,
        check_channels: bool = False,
        check_edited: bool = False,
        chats: Iterable[str] | None = None,
        ignore_chats: Iterable[str] | None = None,
        admin_cache_ttl: float = 300.0,
        max_admin_pages: int = 100,
        shutdown_timeout: float = 5.0,
        **base_kwargs: Any,
    ) -> None:
        super().__init__(**base_kwargs)

        self.enabled = bool(enabled)
        self.action: Action = self._normalize_action(action)
        self.actions: dict[str, Action] = {}
        for violation, violation_action in (actions or {}).items():
            self.actions[self._violation_key(violation)] = self._normalize_action(
                violation_action
            )

        self.mute_seconds = float(mute_seconds) if mute_seconds is not None else None
        self.warn_text = warn_text
        self.delete_on_action = bool(delete_on_action)
        self.delete_during_mute = bool(delete_during_mute)
        self.ignore_admins = bool(ignore_admins)
        self.ignore_bots = bool(ignore_bots)
        self.check_private = bool(check_private)
        self.check_channels = bool(check_channels)
        self.check_edited = bool(check_edited)
        self.chats = set(chats) if chats is not None else None
        self.ignore_chats = set(ignore_chats or ())
        self.admin_cache_ttl = max(0.0, float(admin_cache_ttl))
        self.max_admin_pages = max(1, int(max_admin_pages))
        self.shutdown_timeout = max(0.1, float(shutdown_timeout))

        self._admin_cache: dict[str, tuple[float, frozenset[str]]] = {}
        # key -> (methods, unban task)
        self._ban_tasks: dict[tuple[str, str], tuple["Methods", asyncio.Task]] = {}
        self._action_tasks: set[asyncio.Task] = set()

    # ═══════════════════════════════════
    # region 🎛️ Settings | تنظیمات
    # ═══════════════════════════════════

    @staticmethod
    def _normalize_action(action: str) -> Action:
        """نرمال‌سازی نام اکشن و اعتبارسنجی آن"""
        value = str(action).strip().lower()
        if value == "kick":
            value = "mute"
        if value not in _VALID_ACTIONS:
            raise ValueError(
                f"اکشن نامعتبر: {action!r} - مجازها: {sorted(_VALID_ACTIONS)}"
            )
        return cast(Action, value)

    @staticmethod
    def _violation_key(violation: SpamViolation | str) -> str:
        """تبدیل enum/نام/مقدار تخلف به کلید یکسان"""
        if isinstance(violation, SpamViolation):
            return violation.value
        key = str(violation).strip().lower()
        for item in SpamViolation:
            if key in (item.value, item.name.lower()):
                return item.value
        raise ValueError(f"نوع تخلف ناشناخته: {violation!r}")

    def enable(self) -> None:
        """فعال کردن سیستم"""
        self.enabled = True

    def disable(self) -> None:
        """غیرفعال کردن سیستم"""
        self.enabled = False

    def action_for(self, violation: SpamViolation | None) -> Action:
        """اکشن مناسب برای یک نوع تخلف"""
        if violation is not None:
            override = self.actions.get(violation.value)
            if override is not None:
                return override
        return self.action

    def _rule_for(self, violation: SpamViolation | None) -> AntiSpamRule | None:
        if violation is None:
            return None
        for rule in self.rules:
            if rule.violation == violation:
                return rule
        return None

    def _mute_duration_for(self, violation: SpamViolation | None) -> float:
        if self.mute_seconds is not None:
            return self.mute_seconds
        rule = self._rule_for(violation)
        return float(rule.mute_duration) if rule is not None else float(self.mute_duration)

    @property
    def pending_bans(self) -> tuple[tuple[str, str], ...]:
        """کاربرانی که در حال سکوت موقت هستند"""
        return tuple(self._ban_tasks)

    def reset(
        self,
        chat_id: str | None = None,
        user_id: str | None = None,
    ) -> None:
        """ریست آمار و کش ادمین‌ها"""
        super().reset(chat_id, user_id)
        if chat_id is None:
            self._admin_cache.clear()
        else:
            self._admin_cache.pop(chat_id, None)

    # endregion

    # ═══════════════════════════════════
    # region 🛡️ Main API | ورودی اصلی
    # ═══════════════════════════════════

    async def inspect(self, message: "Message") -> bool:
        """
        بررسی یک پیام یوزربات و اجرای اکشن در صورت اسپم بودن.

        Returns
        -------
        bool
            ``True`` یعنی پیام به عنوان اسپم مصرف شد و نباید به هندلرها برسد.
        """
        if not self.enabled:
            return False

        chat_id = self._chat_of(message)
        user_id = self._user_of(message)
        if not chat_id or not user_id:
            return False

        if self._is_own(message):
            return False
        if self._is_event(message):
            return False
        if not self.check_edited and self._is_edited(message):
            return False
        if not self._should_check(message, chat_id):
            return False
        if self.ignore_bots and self._author_type(message) == "Bot":
            return False
        if self._author_type(message) == "Service":
            return False

        if self.ignore_admins and await self._is_admin(message.methods, chat_id, user_id):
            return False

        is_spam, reason, violation = self.check(
            chat_id=chat_id,
            user_id=user_id,
            message=self._text_of(message),
            is_private=self._is_private(message, chat_id),
        )
        if not is_spam:
            return False

        if violation is None:
            # کاربر همین حالا در حالت سکوت است؛ پیامش را هم مدیریت کن.
            self._schedule_muted_delete(message)
            return True

        if self.action_for(violation) != "ignore":
            self._schedule_action(message, reason, violation)
        return True

    # endregion

    # ═══════════════════════════════════
    # region ✅ Checks | بررسی‌های کمکی
    # ═══════════════════════════════════

    def _should_check(self, message: "Message", chat_id: str) -> bool:
        if chat_id in self.ignore_chats:
            return False
        if self.chats is not None and chat_id not in self.chats:
            return False

        if self._is_private(message, chat_id):
            return self.check_private

        chat_type = self._chat_type(message, chat_id)
        if chat_type == "Channel":
            return self.check_channels
        return chat_type == "Group"

    @staticmethod
    def _chat_of(message: "Message") -> str:
        try:
            chat_id = message.object_guid
        except Exception:
            chat_id = None
        if not chat_id:
            try:
                chat_id = message.get("chat_updates.0.object_guid")
            except Exception:
                chat_id = None
        return chat_id or ""

    @staticmethod
    def _user_of(message: "Message") -> str:
        try:
            user_id = message.author_guid
        except Exception:
            user_id = None
        return user_id or ""

    @staticmethod
    def _is_own(message: "Message") -> bool:
        try:
            return bool(message.is_mine)
        except Exception:
            return False

    @staticmethod
    def _is_event(message: "Message") -> bool:
        try:
            return bool(message.is_event)
        except Exception:
            return False

    @staticmethod
    def _is_edited(message: "Message") -> bool:
        try:
            return bool(message.is_edited)
        except Exception:
            return False

    @staticmethod
    def _author_type(message: "Message") -> str | None:
        try:
            return message.author_type
        except Exception:
            return None

    @staticmethod
    def _chat_type(message: "Message", chat_id: str) -> str:
        try:
            chat_type = message.chat_type
        except Exception:
            chat_type = None
        if chat_type:
            return chat_type
        if chat_id.startswith("g0"):
            return "Group"
        if chat_id.startswith("c0"):
            return "Channel"
        if chat_id.startswith("u0"):
            return "User"
        return "Unknown"

    def _is_private(self, message: "Message", chat_id: str) -> bool:
        try:
            if message.is_user:
                return True
        except Exception:
            pass
        return chat_id.startswith("u0")

    @staticmethod
    def _text_of(message: "Message") -> str:
        """متن خام پیام؛ برای پیام غیرمتنی رشتهٔ ``"None"`` برنمی‌گرداند."""
        try:
            text = message.get("message_updates.0.message.text")
        except Exception:
            text = None
        return text if isinstance(text, str) else ""

    # endregion

    # ═══════════════════════════════════
    # region 🚦 Admin cache | کش ادمین‌ها
    # ═══════════════════════════════════

    async def _is_admin(
        self,
        methods: "Methods",
        chat_id: str,
        user_id: str,
    ) -> bool:
        # فقط گروه‌ها لیست ادمین دارند.
        if not chat_id.startswith("g0"):
            return False

        now = time.time()
        cached = self._admin_cache.get(chat_id)
        if cached is not None and cached[0] > now:
            return user_id in cached[1]

        try:
            admins = await self._load_admins(methods, chat_id)
        except Exception as error:
            await self._report(methods, error)
            # A short negative cache prevents error flooding on every message
            # when the account cannot read the admin list (e.g. no access).
            if self.admin_cache_ttl > 0:
                self._admin_cache[chat_id] = (
                    now + min(60.0, self.admin_cache_ttl),
                    frozenset(),
                )
            return False

        if self.admin_cache_ttl > 0:
            self._admin_cache[chat_id] = (
                now + self.admin_cache_ttl,
                frozenset(admins),
            )
        return user_id in admins

    async def _load_admins(self, methods: "Methods", chat_id: str) -> set[str]:
        admins: set[str] = set()
        start_id: str | None = None

        for _ in range(self.max_admin_pages):
            result = await methods.getChatAdminMembers(
                objectGuid=chat_id,
                startId=start_id,
            )
            if not isinstance(result, dict):
                break

            for member in result.get("in_chat_members") or ():
                if isinstance(member, dict):
                    member_guid = member.get("member_guid")
                else:
                    member_guid = getattr(member, "member_guid", None)
                if member_guid:
                    admins.add(member_guid)

            if not result.get("has_continue"):
                break

            next_start_id = result.get("next_start_id")
            if not next_start_id or next_start_id == start_id:
                break
            start_id = next_start_id

        return admins

    # endregion

    # ═══════════════════════════════════
    # region ⚡ Actions | اجرای اکشن‌ها
    # ═══════════════════════════════════

    def _schedule_action(
        self,
        message: "Message",
        reason: str | None,
        violation: SpamViolation,
    ) -> None:
        task = asyncio.create_task(self._run_action(message, reason, violation))
        self._track_task(task)

    def _schedule_muted_delete(self, message: "Message") -> None:
        if not self.delete_during_mute:
            return
        if self.action_for(None) == "ignore":
            return
        task = asyncio.create_task(self._delete(message))
        self._track_task(task)

    def _track_task(self, task: asyncio.Task) -> None:
        self._action_tasks.add(task)
        task.add_done_callback(self._action_tasks.discard)

    async def _run_action(
        self,
        message: "Message",
        reason: str | None,
        violation: SpamViolation,
    ) -> None:
        try:
            await self._act(message, reason, violation)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            await self._report(message.methods, error, message)

    async def _act(
        self,
        message: "Message",
        reason: str | None,
        violation: SpamViolation,
    ) -> None:
        action = self.action_for(violation)

        if action == "warn":
            await self._warn(message, reason)
            if self.delete_on_action:
                await self._delete(message)
            return

        if action == "delete":
            await self._delete(message)
            return

        if action in ("mute", "ban"):
            if self.delete_on_action:
                await self._delete(message)
            duration = (
                self._mute_duration_for(violation) if action == "mute" else None
            )
            await self._ban(
                methods=message.methods,
                chat_id=self._chat_of(message),
                user_id=self._user_of(message),
                duration=duration,
            )

    async def _delete(self, message: "Message") -> None:
        try:
            await message.delete(delete_for_all=True)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            await self._report(message.methods, error, message)

    async def _warn(self, message: "Message", reason: str | None) -> None:
        try:
            text = self.warn_text.format(
                reason=reason or "",
                user=self._user_of(message),
                chat=self._chat_of(message),
            )
        except (KeyError, IndexError, ValueError):
            text = f"{self.warn_text} {reason}".strip() if reason else self.warn_text
        try:
            await message.reply(text)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            await self._report(message.methods, error, message)

    # endregion

    # ═══════════════════════════════════
    # region 🚫 Ban / Unban | اخراج و بازگردانی
    # ═══════════════════════════════════

    async def _ban(
        self,
        methods: "Methods",
        chat_id: str,
        user_id: str,
        duration: float | None,
    ) -> None:
        # بن فقط روی گروه معنا دارد.
        if not chat_id.startswith("g0") or not user_id:
            return

        key = (chat_id, user_id)

        try:
            await methods.banChatMember(
                objectGuid=chat_id,
                memberGuid=user_id,
                action="Set",
            )
        except asyncio.CancelledError:
            raise
        except Exception as error:
            await self._report(methods, error)
            return

        # فقط بعد از بن موفق، آنبن قبلی لغو می‌شود تا اگر این درخواست شکست
        # خورد، کاربر با یک آنبنِ ازدست‌رفته بن‌شده باقی نماند.
        self._cancel_ban_task(key)

        if duration is None:
            return

        task = asyncio.create_task(
            self._unban_later(methods, chat_id, user_id, float(duration))
        )
        self._ban_tasks[key] = (methods, task)

    async def _unban_later(
        self,
        methods: "Methods",
        chat_id: str,
        user_id: str,
        duration: float,
    ) -> None:
        key = (chat_id, user_id)
        try:
            await asyncio.sleep(max(0.0, duration))
            await methods.banChatMember(
                objectGuid=chat_id,
                memberGuid=user_id,
                action="Unset",
            )
        except asyncio.CancelledError:
            raise
        except Exception as error:
            await self._report(methods, error)
        finally:
            current = asyncio.current_task()
            stored = self._ban_tasks.get(key)
            if stored is not None and stored[1] is current:
                self._ban_tasks.pop(key, None)

    def _cancel_ban_task(self, key: tuple[str, str]) -> None:
        stored = self._ban_tasks.pop(key, None)
        if stored is not None:
            stored[1].cancel()

    async def shutdown(self) -> None:
        """
        آزادسازی منابع هنگام خاموشی.

        پاکسازی خودکار را متوقف می‌کند، اکشن‌های در جریان را کنسل می‌کند و
        برای سکوت‌های موقتِ باقی‌مانده تلاش می‌کند عضو را آنبن کند تا کسی
        به خاطر خاموش شدن اکانت، بن‌شده باقی نماند.
        """
        await self.stop_auto_clear()

        tasks = list(self._action_tasks)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._action_tasks.clear()

        pending = list(self._ban_tasks.items())
        self._ban_tasks.clear()
        releases = []
        for (chat_id, user_id), (methods, task) in pending:
            task.cancel()
            releases.append(self._release_ban(methods, chat_id, user_id))
        if releases:
            await asyncio.gather(*releases, return_exceptions=True)

        self._admin_cache.clear()

    async def _release_ban(
        self,
        methods: "Methods",
        chat_id: str,
        user_id: str,
    ) -> None:
        try:
            await asyncio.wait_for(
                methods.banChatMember(
                    objectGuid=chat_id,
                    memberGuid=user_id,
                    action="Unset",
                ),
                timeout=self.shutdown_timeout,
            )
        except (TimeoutError, asyncio.CancelledError):
            pass
        except Exception:
            pass

    # endregion

    async def _report(
        self,
        methods: "Methods",
        error: Exception,
        update: "Message | None" = None,
    ) -> None:
        """گزارش خطا با استفاده از on_error کاربر (بدون کرش کردن سوکت)."""
        try:
            await methods._process_on_error(e=error, update=update)  # type: ignore[arg-type]
        except Exception:
            print(f"[fast_rub.pyrubi.antispam] {error}")


UserBotAntiSpam = AntiSpam

__all__ = ["AntiSpam", "UserBotAntiSpam", "SpamViolation", "AntiSpamRule"]
