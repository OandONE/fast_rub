
class GetMe:
    async def get_me(self: "fast_rub.Client"):
        result = await self.send_request(method="getMe", request_type="post")
        return result
