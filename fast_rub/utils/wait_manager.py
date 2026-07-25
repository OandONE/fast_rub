from typing import Literal
from collections.abc import Callable
import time

from .utils import Utils

class WaitManager:
    """مدیریت هوشمند wait_send با کانال‌های ترافیک جداگانه"""
    def __init__(
        self,
        low_traffic: int = 60,
        medium_traffic: int = 100,
        low_wait: float = 0.0,
        medium_wait: float = 1.0,
        high_wait: float = 3.0,
        time_window: float = 60.0,
        auto_track: bool = False,

        sending: bool = True,
        banning: bool = False,
        forwarding: bool = False,
        uploading: bool = False,
        editing: bool = False,
        deleting: bool = False,

        per_chat: bool = True,
        track_after_send: bool = False,

        sleep_callback: Callable | None = None
    ):
        self.low_traffic = low_traffic
        self.medium_traffic = medium_traffic
        self.low_wait = low_wait
        self.medium_wait = medium_wait
        self.high_wait = high_wait
        self.time_window = time_window
        self.auto_track = auto_track

        self.sending = sending
        self.banning = banning
        self.forwarding = forwarding
        self.uploading = uploading
        self.editing = editing
        self.deleting = deleting

        self.per_chat = per_chat
        self.track_after_send = track_after_send

        self.sleep_callback = sleep_callback

        self._traffic: dict[str, dict[str, list[float]]] = {
            "sending": {},
            "banning": {},
            "forwarding": {},
            "uploading": {},
            "editing": {},
            "deleting": {},
        }

    def add_traffic(
        self,
        count: int | None = None,
        channel: Literal["sending", "banning", "forwarding", "uploading", "editing", "deleting"] = "sending",
        chat_id: str | None = None
    ):
        """ثبت ترافیک در یک کانال خاص (و چت خاص)"""
        if channel not in self._traffic:
            raise ValueError(f"کانال نامعتبر: {channel}")

        key = chat_id if (self.per_chat and chat_id) else "_global"
        if key not in self._traffic[channel]:
            self._traffic[channel][key] = []

        n = count if count is not None else 1
        now = time.time()
        for _ in range(n):
            self._traffic[channel][key].append(now)
        self._clean_old(channel, key)

    def track(self, chat_id: str | None = None):
        """برای auto_track"""
        self.add_traffic(chat_id=chat_id)

    def _clean_old(self, channel: str, chat_id: str = "_global"):
        if chat_id in self._traffic[channel]:
            cutoff = time.time() - self.time_window
            self._traffic[channel][chat_id] = [
                t for t in self._traffic[channel][chat_id] if t > cutoff
            ]

    def _get_channel_traffic(self, channel: str, chat_id: str | None = None) -> int:
        key = chat_id if (self.per_chat and chat_id) else "_global"
        self._clean_old(channel, key)
        return len(self._traffic[channel].get(key, []))

    async def get_time(
        self,
        channel: Literal["sending", "banning", "forwarding", "uploading", "editing", "deleting"] = "sending",
        chat_id: str | None = None
    ) -> float:
        if not getattr(self, channel, False) and channel != "sending":
            return 0.0

        count = self._get_channel_traffic(channel, chat_id)

        # Sleep Callback
        if self.sleep_callback:
            result = await Utils.run_handler(
                self.sleep_callback,
                channel=channel,
                messages_count=count,
                last_time=self._traffic[channel].get(chat_id or "_global", [0])[-1] if self._traffic[channel].get(chat_id or "_global") else None,
                total_requests=sum(len(v) for v in self._traffic[channel].values()),
                time_window=self.time_window,
                low_traffic=self.low_traffic,
                medium_traffic=self.medium_traffic,
                low_wait=self.low_wait,
                medium_wait=self.medium_wait,
                high_wait=self.high_wait,
            )
            if isinstance(result, (int, float)):
                return float(result)

        if count <= self.low_traffic:
            return self.low_wait
        elif count <= self.medium_traffic:
            return self.medium_wait
        else:
            return self.high_wait

    def reset(
        self,
        channel: str | None = None,
        chat_id: str | None = None
    ):
        """ریست یک کانال/چت یا همه"""
        if channel and chat_id:
            self._traffic[channel].pop(chat_id, None)
        elif channel:
            self._traffic[channel].clear()
        else:
            for ch in self._traffic:
                self._traffic[ch].clear()
