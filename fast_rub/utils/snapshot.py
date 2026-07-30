import json
import os
import asyncio
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core import Client


class SnapshotManager:
    """مدیریت Version Control برای ربات"""
    
    def __init__(
        self,
        client: "Client",
        folder: str = "snapshots"
    ):
        self.client = client
        self.folder = folder
        os.makedirs(folder, exist_ok=True)
    
    async def save(self, name: str) -> str:
        """ذخیره Snapshot از تنظیمات فعلی"""
        data = {
            "version": getattr(self.client, "version", "unknown"),
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "client": {
                "parse_mode": getattr(self.client, "main_parse_mode", None),
                "timeout": getattr(self.client, "time_out", None),
                "ssl_verify": getattr(self.client, "ssl_verify", True),
                "poll_interval": getattr(self.client, "poll_interval", 0.0),
            },
            "wait_manager": self._snapshot_wait_manager(),
            "middlewares": self._snapshot_middlewares(),
            "conversations": self._snapshot_conversations(),
            "plugins": self._snapshot_plugins(),
            "cache": self._snapshot_cache(),
            "scheduler": self._snapshot_scheduler(),
        }
        
        filepath = os.path.join(self.folder, f"{name}.json")
        await asyncio.to_thread(
            lambda: json.dump(data, open(filepath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        )
        
        return filepath
    
    async def load(self, name: str) -> dict | None:
        """بارگذاری یه Snapshot"""
        filepath = os.path.join(self.folder, f"{name}.json")
        if not os.path.exists(filepath):
            return None
        
        return await asyncio.to_thread(
            lambda: json.load(open(filepath, encoding="utf-8"))
        )
    
    async def list_all(self) -> list[str]:
        """لیست همه Snapshotها"""
        if not os.path.exists(self.folder):
            return []
        
        files = os.listdir(self.folder)
        return [f[:-5] for f in files if f.endswith(".json")]
    
    async def delete(self, name: str) -> bool:
        """حذف یه Snapshot"""
        filepath = os.path.join(self.folder, f"{name}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
    
    def _snapshot_wait_manager(self) -> dict:
        wm = self.client.wait_manager
        if not wm:
            return {}
        return {
            "low_traffic": wm.low_traffic,
            "medium_traffic": wm.medium_traffic,
            "low_wait": wm.low_wait,
            "medium_wait": wm.medium_wait,
            "high_wait": wm.high_wait,
            "time_window": wm.time_window,
            "per_chat": wm.per_chat,
            "track_after_send": wm.track_after_send,
            "sending": wm.sending,
            "banning": wm.banning,
            "forwarding": wm.forwarding,
            "uploading": wm.uploading,
            "editing": wm.editing,
            "deleting": wm.deleting,
        }
    
    def _snapshot_middlewares(self) -> list:
        mm = self.client._middleware_manager
        if not mm:
            return []
        return [
            mw["handler"].name if hasattr(mw["handler"], "name") else str(mw["handler"])
            for mw in mm._middlewares
        ]
    
    def _snapshot_conversations(self) -> list:
        cm = self.client._conversation_manager
        if not cm:
            return []
        return [
            {"name": conv.name, "timeout": conv.timeout}
            for conv in cm._conversations.values()
        ]
    
    def _snapshot_plugins(self) -> list:
        return self.client._loaded_plugins
    
    def _snapshot_cache(self) -> dict:
        cache = self.client.cache
        if not cache:
            return {}
        return {
            "ttl": cache.ttl,
            "max_size": cache.max_size,
        }
    
    def _snapshot_scheduler(self) -> int:
        sched = self.client.scheduler
        if not sched:
            return 0
        return sched.count

    async def restore(self, name: str) -> bool:
        """بارگذاری و اعمال Snapshot روی Client"""
        data = await self.load(name)
        if not data:
            return False
        
        # Client
        client_data: dict = data.get("client", {})
        if client_data.get("parse_mode"):
            self.client.main_parse_mode = client_data["parse_mode"]
        if client_data.get("timeout"):
            self.client.time_out = client_data["timeout"]
        if client_data.get("ssl_verify") is not None:
            self.client.ssl_verify = client_data["ssl_verify"]
        if client_data.get("poll_interval") is not None:
            self.client.poll_interval = client_data["poll_interval"]
        
        # WaitManager
        wm_data: dict = data.get("wait_manager", {})
        if wm_data and self.client.wait_manager:
            wm = self.client.wait_manager
            for key, value in wm_data.items():
                if hasattr(wm, key):
                    setattr(wm, key, value)
        
        # Cache
        cache_data: dict = data.get("cache", {})
        if cache_data and self.client.cache:
            if cache_data.get("ttl"):
                self.client.cache.ttl = cache_data["ttl"]
            if cache_data.get("max_size"):
                self.client.cache.max_size = cache_data["max_size"]
        
        return True
