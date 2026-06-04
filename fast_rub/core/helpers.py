import asyncio
from typing import Any, TYPE_CHECKING, Literal, Optional, Union

from collections.abc import Callable, Coroutine

from ..utils import Utils

if TYPE_CHECKING:
    from .client import Client
    from ..types import msg_update


async def _send_helper(
    self: "Client",
    func: Callable[..., Coroutine[Any, Any, Any]],
    channel: Literal["sending", "banning", "forwarding", "uploading", "editing", "deleting"] = "sending",
    return_task: bool = False,
    wait_send: float | None = None,
    **kwargs: Any
) -> Union["msg_update", asyncio.Task["msg_update"], Any]:
    """تابع کمکی برای متدهای ارسال"""
    
    async def _active():
        for key in ("chat_id", "from_chat_id", "to_chat_id", "user_id", "sender_id"):
            if key in kwargs and kwargs[key] is not None:
                Utils.check_id_raise(kwargs[key])
        
        if self.wait_manager and self.wait_manager.track_after_send:
            chat_id = kwargs.get("chat_id") or kwargs.get("to_chat_id")
            _chat_id = chat_id if self.wait_manager.per_chat else None
            self.wait_manager.add_traffic(channel=channel, chat_id=_chat_id)
        
        wait = await self._wait(wait_send)
        if wait:
            await asyncio.sleep(wait)
        
        return await func()
    
    if return_task:
        return asyncio.create_task(_active())
    else:
        return await _active()
