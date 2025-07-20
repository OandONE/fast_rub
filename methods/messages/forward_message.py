

class ForwardMessage:
    async def forward_message(
        self: "fast_rub.Client",
        from_chat_id: str,
        message_id: str,
        to_chat_id: str,
        disable_notification: bool = False,
    ):
        data = {
            "from_chat_id": from_chat_id,
            "message_id": message_id,
            "to_chat_id": to_chat_id,
            "disable_notification": disable_notification,
        }
        result = await self.send_request("frowardMessage", data, request_type="post")
        return result