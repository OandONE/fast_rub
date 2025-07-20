from typing import Optional
import httpx

class SendRequest:
    async def send_request(self: "fast_rub.Client", method, data: Optional[dict] = {}, request_type="get"):
        url = f"https://botapi.rubika.ir/v3/{self.token}/{method}"
        if self.user_agent != None:
            headers = {"'User-Agent'": self.user_agent}
        else:
            headers = None
        if request_type == "post":
            async with httpx.AsyncClient() as cl:
                result = await cl.post(url, headers=headers)
                return result.json()