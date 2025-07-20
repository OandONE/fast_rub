

class EditMessageText:
    async def edit_message_text(self: "fast_rub.Client", chat_id: str, message_id: str, text: str):
        data = {"chat_id": chat_id, "message_id": message_id, "text": text}
        result = await self.send_request("editMessageText", data, request_type="post")
        return result