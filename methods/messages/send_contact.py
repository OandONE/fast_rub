from typing import Optional

class SendContact:
    async def send_contact(
        self: "fast_rub.Client",
        chat_id: str,
        first_name: str,
        last_name: str,
        phone_number: str,
        chat_keypad: str,
        chat_keypad_type: str,
        inline_keypad,
        reply_to_message_id: Optional[str] = None,
        disable_notification: bool = False,
    ):
        data = {
            "chat_id": chat_id,
            "first_name": first_name,
            "last_name": last_name,
            "phone_number": phone_number,
            "chat_keypad": chat_keypad,
            "disable_notification": disable_notification,
            "chat_keypad_type": chat_keypad_type,
            "inline_keypad": inline_keypad,
            "reply_to_message_id": reply_to_message_id,
        }
        result = await self.send_request("sendContact", data, request_type="post")
        return result