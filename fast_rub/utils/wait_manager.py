from typing import Optional, Literal
import time

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
        count: Optional[int] = None,
        channel: Literal["sending", "banning", "forwarding", "uploading", "editing", "deleting"] = "sending",
        chat_id: Optional[str] = None
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

    def track(self, chat_id: Optional[str] = None):
        """برای auto_track"""
        self.add_traffic(chat_id=chat_id)

    def _clean_old(self, channel: str, chat_id: str = "_global"):
        if chat_id in self._traffic[channel]:
            cutoff = time.time() - self.time_window
            self._traffic[channel][chat_id] = [
                t for t in self._traffic[channel][chat_id] if t > cutoff
            ]

    def _get_channel_traffic(self, channel: str, chat_id: Optional[str] = None) -> int:
        key = chat_id if (self.per_chat and chat_id) else "_global"
        self._clean_old(channel, key)
        return len(self._traffic[channel].get(key, []))

    def get_time(
        self,
        channel: Literal[
            "sending", "banning",
            "forwarding", "uploading",
            "editing", "deleting"
        ] = "sending",
        chat_id: Optional[str] = None
    ) -> float:
        """دریافت wait_send برای یک کانال و چت خاص"""
        if not getattr(self, channel, False) and channel != "sending":
            return 0.0

        count = self._get_channel_traffic(channel, chat_id)

        if count <= self.low_traffic:
            return self.low_wait
        elif count <= self.medium_traffic:
            return self.medium_wait
        else:
            return self.high_wait

    def reset(
        self,
        channel: Optional[str] = None,
        chat_id: Optional[str] = None
    ):
        """ریست یک کانال/چت یا همه"""
        if channel and chat_id:
            self._traffic[channel].pop(chat_id, None)
        elif channel:
            self._traffic[channel].clear()
        else:
            for ch in self._traffic:
                self._traffic[ch].clear()
