

class SendPoll:
    async def send_poll(self: "fast_rub.Client", chat_id: str, question: str, options: list):
        data = {"chat_id": chat_id, "question": question, "options": options}
        result = await self.send_request("sendPoll", data, request_type="post")
        return result