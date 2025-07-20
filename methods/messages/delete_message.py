

class DeleteMessage:
    async def delete_message(self: "fast_rub.Client", chat_id: str, message_id: str):
        data = {"chat_id": chat_id, "message_id": message_id}
        result = await self.send_request("deleteMessage", data, request_type="post")
        return result