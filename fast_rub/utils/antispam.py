import re
import time
import asyncio
from collections import defaultdict, deque
from typing import Optional, Dict, Tuple, List
from enum import Enum


class SpamViolation(Enum):
    """انواع تخلفات اسپم"""
    FLOOD = "flood"              # پیام پشت سر هم
    RATE_LIMIT = "rate_limit"    # تعداد بیش از حد
    DUPLICATE = "duplicate"      # پیام تکراری
    LONG_MESSAGE = "long_msg"    # پیام خیلی طولانی
    LINK_SPAM = "link_spam"      # لینک اسپم
    MENTION_SPAM = "mention_spam"  # منشن اسپم
    BOT_SPAM = "bot_spam"       # دستورات ربات


class AntiSpamRule:
    """یه قانون ضد اسپم"""
    def __init__(self, violation: SpamViolation, max_count: int, window: float, mute_duration: float):
        self.violation = violation
        self.max_count = max_count
        self.window = window
        self.mute_duration = mute_duration


class AntiSpam:
    """
    سیستم ضد اسپم پیشرفته برای ربات‌های روبیکا.

    ویژگی‌ها:
    - تشخیص Flood (پیام پشت سر هم)
    - تشخیص Rate Limit (تعداد بیش از حد)
    - تشخیص پیام تکراری
    - تشخیص پیام طولانی
    - تشخیص لینک و منشن اسپم
    - سکوت خودکار با مدت زمان قابل تنظیم
    - پشتیبانی از گروه و پی‌وی
    - پاکسازی خودکار حافظه
    - قابلیت افزودن قوانین سفارشی
    """
    RUBIKA_LINK = re.compile(r"rubika\.ir/[^\s]+")
    USERNAME = re.compile(r"@[a-zA-Z0-9_]{4,32}")
    MENTION = re.compile(r"\[([^\]]+)\]\(u[a-zA-Z0-9]+\)")

    def __init__(
        self,
        flood_max: int = 3,
        flood_window: float = 2.0,
        rate_max: int = 5,
        rate_window: float = 10.0,
        duplicate_window: float = 30.0,
        max_message_length: int = 2000,
        link_max: int = 3,
        link_window: float = 60.0,
        mention_max: int = 5,
        mention_window: float = 60.0,
        
        mute_duration: float = 60.0,
        auto_clear_interval: int = 30,
    ):
        self.rules: List[AntiSpamRule] = [
            AntiSpamRule(SpamViolation.FLOOD, flood_max, flood_window, mute_duration),
            AntiSpamRule(SpamViolation.RATE_LIMIT, rate_max, rate_window, mute_duration),
            AntiSpamRule(SpamViolation.LINK_SPAM, link_max, link_window, mute_duration),
            AntiSpamRule(SpamViolation.MENTION_SPAM, mention_max, mention_window, mute_duration),
        ]
        
        self.duplicate_window = duplicate_window
        self.max_message_length = max_message_length
        self.mute_duration = mute_duration
        
        self._messages: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max(rate_max, link_max, mention_max) * 2))
        self._muted: Dict[str, float] = {}
        self._last_messages: Dict[str, Tuple[float, str]] = {}
        
        self._auto_clear_task: Optional[asyncio.Task] = None
        self._auto_clear_interval = auto_clear_interval
    
    def add_rule(self, rule: AntiSpamRule):
        """افزودن قانون سفارشی"""
        self.rules.append(rule)
    
    def remove_rule(self, violation: SpamViolation):
        """حذف یه قانون"""
        self.rules = [r for r in self.rules if r.violation != violation]
    
    def check(
        self,
        chat_id: str,
        user_id: str,
        message: str,
        is_private: bool = False
    ) -> Tuple[bool, Optional[str], Optional[SpamViolation]]:
        """
        بررسی اسپم بودن پیام.
        
        Args:
            chat_id: آیدی چت
            user_id: آیدی کاربر (برای پی‌وی همون chat_id)
            message: متن پیام
            is_private: آیا پی‌وی هست؟
            
        Returns:
            (is_spam, reason, violation_type)
        """
        now = time.time()
        key = f"{chat_id}:{user_id}" if not is_private else f"private:{chat_id}"

        if key in self._muted:
            if now < self._muted[key]:
                remaining = int(self._muted[key] - now)
                return True, f"⏳ {remaining} ثانیه دیگر سکوت هستید.", None
            del self._muted[key]
        
        if len(message) > self.max_message_length:
            self._mute(key, now, self.mute_duration)
            return True, f"📏 پیام بیش از حد طولانی است ({self.max_message_length} کاراکتر).", SpamViolation.LONG_MESSAGE
        
        if key in self._last_messages:
            last_time, last_msg = self._last_messages[key]
            if now - last_time <= self.duplicate_window and last_msg == message:
                return True, "🔄 پیام تکراری.", SpamViolation.DUPLICATE
        
        self._messages[key].append(now)
        self._last_messages[key] = (now, message)
        
        for rule in self.rules:
            count = self._count_violations(key, rule)
            if count >= rule.max_count:
                self._mute(key, now, rule.mute_duration)
                reason = self._get_reason(rule)
                return True, reason, rule.violation
        
        return False, None, None
    
    def _count_violations(self, key: str, rule: AntiSpamRule) -> int:
        """شمارش تخلفات یه قانون خاص"""
        now = time.time()
        
        if rule.violation == SpamViolation.FLOOD:
            return sum(1 for t in self._messages[key] if now - t <= rule.window)
        
        elif rule.violation == SpamViolation.RATE_LIMIT:
            return sum(1 for t in self._messages[key] if now - t <= rule.window)
        
        elif rule.violation == SpamViolation.LINK_SPAM:
            return len(self.RUBIKA_LINK.findall(
                " ".join([""] * len([t for t in self._messages[key] if now - t <= rule.window]))
            ))
        
        elif rule.violation == SpamViolation.MENTION_SPAM:
            return len(self.MENTION.findall(
                " ".join([""] * len([t for t in self._messages[key] if now - t <= rule.window]))
            ))
        
        return 0
    
    def _mute(self, key: str, now: float, duration: float):
        """سکوت کردن کاربر"""
        self._muted[key] = now + duration
    
    def _get_reason(self, rule: AntiSpamRule) -> str:
        """دریافت پیام مناسب برای هر تخلف"""
        reasons = {
            SpamViolation.FLOOD: f"⚡ ارسال سریع پیام. {int(rule.mute_duration)} ثانیه سکوت شدید.",
            SpamViolation.RATE_LIMIT: f"📊 تعداد پیام‌های بیش از حد. {int(rule.mute_duration)} ثانیه سکوت شدید.",
            SpamViolation.LINK_SPAM: f"🔗 لینک اسپم. {int(rule.mute_duration)} ثانیه سکوت شدید.",
            SpamViolation.MENTION_SPAM: f"👤 منشن اسپم. {int(rule.mute_duration)} ثانیه سکوت شدید.",
            SpamViolation.DUPLICATE: "🔄 پیام تکراری.",
            SpamViolation.LONG_MESSAGE: f"📏 پیام بیش از حد طولانی.",
        }
        return reasons.get(rule.violation, f"🚫 اسپم. {int(rule.mute_duration)} ثانیه سکوت شدید.")
    
    def unmute(self, chat_id: str, user_id: Optional[str] = None):
        """لغو سکوت کاربر"""
        key = f"{chat_id}:{user_id}" if user_id else f"private:{chat_id}"
        self._muted.pop(key, None)
    
    def is_muted(self, chat_id: str, user_id: Optional[str] = None) -> bool:
        """چک وضعیت سکوت"""
        key = f"{chat_id}:{user_id}" if user_id else f"private:{chat_id}"
        if key in self._muted:
            if time.time() < self._muted[key]:
                return True
            del self._muted[key]
        return False
    
    def reset(self, chat_id: Optional[str] = None, user_id: Optional[str] = None):
        """ریست آمار"""
        if chat_id and user_id:
            key = f"{chat_id}:{user_id}"
            self._messages.pop(key, None)
            self._muted.pop(key, None)
            self._last_messages.pop(key, None)
        elif chat_id:
            keys = [k for k in self._messages if k.startswith(f"{chat_id}:")]
            for k in keys:
                self._messages.pop(k, None)
                self._muted.pop(k, None)
                self._last_messages.pop(k, None)
        else:
            self._messages.clear()
            self._muted.clear()
            self._last_messages.clear()
    
    async def start_auto_clear(self):
        """شروع پاکسازی خودکار"""
        if self._auto_clear_task is None:
            self._auto_clear_task = asyncio.create_task(self._auto_clear_loop())
    
    async def _auto_clear_loop(self):
        """حلقه پاکسازی خودکار"""
        while True:
            await asyncio.sleep(self._auto_clear_interval)
            now = time.time()
            
            expired = [k for k, t in self._muted.items() if now > t]
            for k in expired:
                del self._muted[k]
            
            max_window = max((r.window for r in self.rules), default=60)
            for key in list(self._messages.keys()):
                self._messages[key] = deque(
                    [t for t in self._messages[key] if now - t <= max_window],
                    maxlen=self._messages[key].maxlen
                )
    
    async def stop_auto_clear(self):
        """توقف پاکسازی خودکار"""
        if self._auto_clear_task:
            self._auto_clear_task.cancel()
            try:
                await self._auto_clear_task
            except asyncio.CancelledError:
                pass
            self._auto_clear_task = None
