import asyncio
from typing import Any, TYPE_CHECKING, Literal

from collections.abc import Callable, Coroutine

from ..utils import Utils
from ..types import msg_update

if TYPE_CHECKING:
    from .client import Client


async def _send_helper(
    self: "Client",
    func: Callable[..., Coroutine[Any, Any, Any]],
    channel: Literal["sending", "banning", "forwarding", "uploading", "editing", "deleting"] = "sending",
    return_task: bool = False,
    wait_send: float | None = None,
    **kwargs: Any
) -> msg_update | asyncio.Task[msg_update] | Any:
    """تابع کمکی برای متدهای ارسال"""
    
    async def _active():
        if "text" in kwargs and kwargs["text"] is not None:
            if not await self._trigger_before_send(**kwargs):
                return None

        if self.config.validate_chat_id:
            for key in ("chat_id", "from_chat_id", "to_chat_id", "user_id", "sender_id"):
                if key in kwargs and kwargs[key] is not None:
                    Utils.check_id_raise(kwargs[key])
        
        for key in ("reply_to_message_id", "message_id"):
            if key in kwargs and kwargs[key] is not None:
                Utils.check_message_id_raise(kwargs[key])
        
        if self.wait_manager and self.wait_manager.track_after_send:
            chat_id = kwargs.get("chat_id") or kwargs.get("to_chat_id")
            _chat_id = chat_id if self.wait_manager.per_chat else None
            self.wait_manager.add_traffic(channel=channel, chat_id=_chat_id)
        
        wait = await self._wait(wait_send)
        if wait:
            await asyncio.sleep(wait)
        
        result = await func()

        if "text" in kwargs and kwargs["text"] is not None:
            await self._trigger_after_send(result=result, **kwargs)

        return result
    
    if return_task:
        return asyncio.create_task(_active())
    else:
        return await _active()
