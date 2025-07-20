

class GetChat:
    async def get_chat(self: "fast_rub.Client", chat_id: str):
        data = {"chat_id": chat_id}
        result = await self.send_request("getChat", data, request_type="post")
        return result