from typing import Optional

class SendLocation:
    async def send_location(
        self: "fast_rub.Client",
        chat_id: str,
        latitude: str,
        longitude: str,
        chat_keypad: str,
        disable_notification: Optional[bool] = False,
        reply_to_message_id: Optional[str] = None,
        chat_keypad_type: Optional[str] = None,
    ):
        data = {
            "chat_id": chat_id,
            "latitude": latitude,
            "longitude": longitude,
            "chat_keypad": chat_keypad,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "chat_keypad_type": chat_keypad_type,
        }
        result = await self.send_request("sendLocation", data, request_type="post")
        return result