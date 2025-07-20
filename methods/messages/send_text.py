from typing import Optional

class SendText:
    async def send_text(
        self: "fast_rub.Client",
        text: str,
        chat_id: str,
        disable_notification: Optional[bool] = False,
        reply_to_message_id=None,
    ):
        data = {
            "chat_id": chat_id,
            "text": text,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
        }
        result = await self.send_request("sendMessage", data, request_type="post")
        return result